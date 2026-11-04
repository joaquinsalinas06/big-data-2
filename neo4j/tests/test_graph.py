from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze import PARAMETERS, analyze, diversity, affinity_graph, save_analysis
from load import prepare, load_data
from graph import crud, queries


def event(user, artist):
    return {"user_id": user, "recording_msid": artist, "timestamp": 100,
            "track_metadata": {"artist_name": artist, "track_name": artist}}


class DataTests(unittest.TestCase):
    def test_aggregation_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "datos.jsonl", Path(directory) / "datos.sqlite"
            rows = [event(1, "Artista 🎶")] * 10001
            source.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            meta = prepare(source, output, "prueba", 0)
            self.assertEqual(meta["rows"], 10001)
            with closing(sqlite3.connect(output)) as db:
                self.assertEqual(db.execute("SELECT count FROM listens").fetchone()[0], 10001)
            original = output.read_bytes()
            source.write_text('{"user_id": 1}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare(source, output, "prueba", 0)
            self.assertEqual(output.read_bytes(), original)


class AnalysisTests(unittest.TestCase):
    def test_affinity_and_diversity(self):
        graph = affinity_graph({"A": {1, 2, 3}, "B": {1, 2}, "C": {3, 4}},
                               {**PARAMETERS, "min_common": 1, "neighbors": 1})
        self.assertAlmostEqual(graph["A"]["B"]["weight"], 2 / 3)
        self.assertAlmostEqual(graph["A"]["C"]["weight"], 1 / 4)
        self.assertIsNone(diversity([]))
        self.assertEqual(diversity([9]), 0)
        self.assertAlmostEqual(diversity([8, 8]), 1)

    def test_no_eligible_artists(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "datos.jsonl", Path(directory) / "datos.sqlite"
            source.write_text(json.dumps(event(1, "A")), encoding="utf-8")
            meta = prepare(source, output, "prueba", 0)
            with closing(sqlite3.connect(output)) as db:
                result = analyze(db, meta)
            self.assertEqual(result["communities"], [])
            self.assertIsNone(result["kpis"]["modularidad"])
            self.assertEqual(result["kpis"]["cobertura_recomendaciones"], 0)


@unittest.skipUnless(os.environ.get("NEO4J_INTEGRATION") == "1", "Requiere Neo4j encendido")
class GraphTests(unittest.TestCase):
    def test_repeated_load_analysis_and_crud(self):
        from database import DATABASE, connect
        dataset = "prueba-" + uuid.uuid4().hex
        artists = [dataset + name for name in "ABC"]
        with tempfile.TemporaryDirectory() as directory, connect() as driver, driver.session(database=DATABASE) as session:
            source, output = Path(directory) / "datos.jsonl", Path(directory) / "datos.sqlite"
            rows = [event(-990001, artists[0]), event(-990001, artists[0]), event(-990001, artists[1])]
            rows += [event(-990002, artist) for artist in artists]
            source.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            meta = prepare(source, output, dataset, 0)
            try:
                with closing(sqlite3.connect(output)) as db:
                    load_data(session, db, meta)
                    load_data(session, db, meta)
                    self.assertEqual(session.execute_read(queries.count_listens, dataset),
                                     {"usuarios": 2, "canciones": 3, "relaciones": 5, "escuchas": 6})
                    result = analyze(db, meta, {**PARAMETERS, "min_audience": 1, "min_common": 1})
                session.execute_write(save_analysis, result)
                session.execute_write(save_analysis, result)
                recommended = session.execute_read(queries.recommend_artists, dataset, -990001)
                self.assertEqual(recommended[0]["artista"], artists[2])
                self.assertAlmostEqual(recommended[0]["puntaje"], 0.5)
                for query_fn, args in ((queries.list_artists, (dataset,)),
                                       (queries.get_tracks, (dataset, artists[0])),
                                       (queries.search_artists, (dataset, dataset)),
                                       (queries.filter_listens, (dataset, -990001, 1)),
                                       (queries.recommend_tracks, (dataset, -990001)),
                                       (queries.get_communities, (dataset,)),
                                       (queries.get_bridge_artists, (dataset,)),
                                       (queries.get_user_diversity, (dataset, -990001)),
                                       (queries.find_artist_path, (dataset, artists[0], artists[2])),
                                       (queries.get_indicators, (dataset,))):
                    self.assertTrue(session.execute_read(query_fn, *args))

                incomplete = {**result, "edges": [*result["edges"],
                              {**result["edges"][0], "left": dataset + "ausente"}]}
                with self.assertRaises(ValueError):
                    session.execute_write(save_analysis, incomplete)
                self.assertEqual(session.execute_read(queries.recommend_artists, dataset, -990001), recommended)
                with closing(sqlite3.connect(output)) as db:
                    empty = analyze(db, meta)
                session.execute_write(save_analysis, empty)
                self.assertEqual(session.execute_read(queries.get_communities, dataset), [])
                self.assertIsNone(session.execute_read(queries.get_indicators, dataset)[0]["modularidad"])
                session.execute_write(save_analysis, result)
                for _ in range(2):
                    session.execute_write(crud.create_nodes)
                    session.execute_write(crud.create_relationship)
                    session.execute_write(crud.update_properties, 3)
                    self.assertEqual(session.execute_read(crud.get_listens)[0]["cantidad"], 3)
                    self.assertEqual(session.execute_write(crud.delete_relationship), 1)
                    self.assertEqual(session.execute_write(crud.delete_nodes), 2)
                self.assertEqual(session.execute_read(queries.count_listens, dataset)["escuchas"], 6)
            finally:
                session.execute_write(crud.delete_nodes)
                for label, key, values in (("Usuario", "id", [-990001, -990002]),
                                                  ("Cancion", "id", artists), ("Artista", "nombre", artists)):
                    session.run(f"MATCH (n:{label}) WHERE n.{key} IN $values DETACH DELETE n", values=values).consume()
                session.run("MATCH (c:Comunidad) WHERE c.analisis=$id DETACH DELETE c", id=result["id"] if 'result' in locals() else "").consume()
                session.run("MATCH (a:Analisis {lote:$dataset}) DETACH DELETE a", dataset=dataset).consume()
                session.run("MATCH (l:Lote {id:$dataset}) DETACH DELETE l", dataset=dataset).consume()


if __name__ == "__main__":
    unittest.main()

import os

from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.query import dict_factory

KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "music_dna")


def get_session(keyspace=KEYSPACE):
    hosts = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
    port = int(os.getenv("CASSANDRA_PORT", "9042"))
    profile = ExecutionProfile(
        load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=os.getenv("CASSANDRA_DC", "datacenter1")),
        row_factory=dict_factory,
        request_timeout=60,
    )
    cluster = Cluster(hosts, port=port, execution_profiles={EXEC_PROFILE_DEFAULT: profile})
    return cluster.connect(keyspace)

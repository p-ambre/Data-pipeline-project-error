from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import (StageToRedshiftOperator, LoadFactOperator,
                                LoadDimensionOperator, DataQualityOperator)
from helpers import SqlQueries

# AWS_KEY = os.environ.get('AWS_KEY')
# AWS_SECRET = os.environ.get('AWS_SECRET')

default_args = {
    'owner': 'udacity',
    'dependency_on_past': False,
    'retries': 2,
    'retry_delay':timedelta(minutes=1),
    'catchup': False,
    'email_on_retry': False,
    'start_date': datetime(2019, 1, 12)
}

dag = DAG('s3_to_redshift_dags',
          default_args=default_args,
          description='Load and transform data in Redshift with Airflow',
          schedule_interval='@monthly'
        )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

stage_events_to_redshift = StageToRedshiftOperator(
    task_id='Stage_events',
    dag=dag,
    table="public.staging_events",
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    s3_bucket="udacity-dend",
    s3_key="log_data",
    json="s3://udacity-dend/log_json_path.json"

)

stage_songs_to_redshift = StageToRedshiftOperator(
    task_id='Stage_songs',
    dag=dag,
    table="public.staging_songs",
    redshift_conn_id="redshift",
    aws_credentials_id="aws_credentials",
    s3_bucket="udacity-dend",
    s3_key="song_data/A/A/A",
    json="auto"
)

load_songplays_table = LoadFactOperator(
    task_id='Load_songplays_fact_table',
    dag=dag,
    table="public.songplays",
    redshift_conn_id="redshift",
    truncate_table=True,
    query=SqlQueries.songplay_table_insert
)

load_user_dimension_table = LoadDimensionOperator(
    task_id='Load_user_dim_table',
    dag=dag,
    table="public.users",
    redshift_conn_id="redshift",
    truncate_table=True,
    query=SqlQueries.user_table_insert
)


load_song_dimension_table = LoadDimensionOperator(
    task_id='Load_song_dim_table',
    dag=dag,
    table="public.songs",
    redshift_conn_id="redshift",
    truncate_table=True,
    query=SqlQueries.song_table_insert
)

load_artist_dimension_table = LoadDimensionOperator(
    task_id='Load_artist_dim_table',
    dag=dag,
    table="public.artists",
    redshift_conn_id="redshift",
    truncate_table=True,
    query=SqlQueries.artist_table_insert
)

load_time_dimension_table = LoadDimensionOperator(
    task_id='Load_time_dim_table',
    dag=dag,
    table="public.time",
    redshift_conn_id="redshift",
    truncate_table=True,
    query=SqlQueries.time_table_insert
)

dq_checks = [{'check_sql':"SELECT COUNT(*) FROM users WHERE userid is null", 'expected_result':0},
             {'check_sql':"SELECT COUNT(*) FROM songs WHERE songid is null", 'expected_result':0}]

run_quality_checks = DataQualityOperator(
    task_id='Run_data_quality_checks',
    dag=dag,
    redshift_conn_id="redshift",
    dq_checks=dq_checks
)

end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)

start_operator >> [stage_events_to_redshift, stage_songs_to_redshift] >> \
load_songplays_table >> [load_user_dimension_table,
                         load_song_dimension_table,
                         load_artist_dimension_table,
                         load_time_dimension_table] \
>> run_quality_checks >> end_operator

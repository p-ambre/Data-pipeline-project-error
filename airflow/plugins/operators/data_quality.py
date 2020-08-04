from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class DataQualityOperator(BaseOperator):

    ui_color = '#89DA59'

    @apply_defaults
    def __init__(self,
                 # Define your operators params (with defaults) here
                 redshift_conn_id = "",
                 dq_checks = [],
                 *args, **kwargs):

        super(DataQualityOperator, self).__init__(*args, **kwargs)
        # Mapping params here
        self.checks = dq_checks
        self.redshift_conn_id = redshift_conn_id

    def execute(self, context):
        redshift_hook = PostgresHook("redshift")

        for check in dq_checks:
            validate_sql = check["check_sql"]
            result = check["expected_result"]
            records = redshift_hook.get_records(validate_sql)
            num_records = records[0][0]
            if num_records != result:
                raise ValueError(f"Data quality check failed. Expected result is: {result} | Incorrect result: {num_records}")
            else:
                self.log.info(f"Data quality passed with {records[0][0]} records")

"""Run simulation with CaNS."""
from task_runner import executers
from task_runner.executers import mpi_configuration
from task_runner.utils import loki


class CaNSExecuter(executers.MPIExecuter):

    def __init__(
        self,
        working_dir,
        container_image,
        mpi_config: mpi_configuration.MPIClusterConfiguration,
        loki_logger: loki.LokiLogger,
    ):
        super().__init__(working_dir=working_dir,
                         container_image=container_image,
                         loki_logger=loki_logger,
                         mpi_config=mpi_config,
                         sim_binary="cans",
                         file_type="nml",
                         sim_specific_input_filename="input.nml")
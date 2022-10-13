import parsl
import os
from parsl.app.app import python_app, bash_app
from parsl.config import Config
from parsl.executors import WorkQueueExecutor
from parsl.data_provider.files import File
from parsl.monitoring.monitoring import MonitoringHub
from parsl.addresses import address_by_hostname

wq_config = Config(
    executors=[
        WorkQueueExecutor(
            label="parsl-wq-example",

            # If a project_name is given, then Work Queue will periodically
            # report its status and performance back to the global WQ catalog,
            # which can be viewed here:  http://ccl.cse.nd.edu/software/workqueue/status

            # To disable status reporting, comment out the project_name.
            # project_name="parsl-wq-" + str(uuid.uuid4()),

            # The port number that Work Queue will listen on for connecting workers.
            port=8080,

            # A shared filesystem is not needed when using Work Queue.
            shared_fs=False
        )
    ],
    monitoring=MonitoringHub(
       hub_address=address_by_hostname(),
       hub_port=55055,
       monitoring_debug=False,
       resource_monitoring_interval=10,
   ),
)

parsl.clear()
parsl.load(wq_config)


@bash_app
def generate(outputs=[]):
    return "echo $(( RANDOM )) &> {}".format(outputs[0])

@bash_app
def concat(inputs=[], outputs=[]):
    return "cat {0} > {1}".format(" ".join(i.filepath for i in inputs), outputs[0])

@python_app
def total(inputs=[]):
    total = 0
    with open(inputs[0], 'r') as f:
        for l in f:
            total += int(l)
    return total

# Create 5 files with semi-random numbers
output_files = []
for i in range (5):
     output_files.append(generate(outputs=[File(os.path.join(os.getcwd(), 'random-%s.txt' % i))]))

# Concatenate the files into a single file
cc = concat(inputs=[i.outputs[0] for i in output_files],
            outputs=[File(os.path.join(os.getcwd(), 'combined.txt'))])

# Calculate the sum of the random numbers
total = total(inputs=[cc.outputs[0]])

print (total.result())
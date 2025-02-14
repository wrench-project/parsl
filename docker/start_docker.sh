docker run --cpus=1 --name parsl-worker-1 -d -p 2222:22 -v $(pwd)/output:$(pwd)/output -v $(pwd)/data:$(pwd)/data -v $(pwd)/logs:/root/logs parsl-worker 2
docker run --cpus=1 --name parsl-worker-2 -d -p 2223:22 -v $(pwd)/output:$(pwd)/output -v $(pwd)/data:$(pwd)/data -v $(pwd)/logs:/root/logs parsl-worker 1

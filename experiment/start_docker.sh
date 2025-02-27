docker run -d -p 2222:22 -v $(pwd)/data:$(pwd)/data -v $(pwd)/output:$(pwd)/output parsl-worker
docker run -d -p 2223:22 -v $(pwd)/data:$(pwd)/data -v $(pwd)/output:$(pwd)/output parsl-worker

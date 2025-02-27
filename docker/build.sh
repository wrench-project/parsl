if [ $# -eq 1 ]; then
  docker build --target builder -t parsl-worker --build-arg CACHEBUST=$(date +%s) .
else
  docker build --target builder -t parsl-worker .
fi

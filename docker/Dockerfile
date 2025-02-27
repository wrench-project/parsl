FROM continuumio/miniconda3 AS base

# Install dependencies
RUN apt-get update && apt-get install -y openssh-server stress-ng build-essential

RUN conda install -y python==3.12.8

# Configure SSH server
RUN mkdir /var/run/sshd
RUN echo 'root:redhat' | chpasswd

#Set no password for user login
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
EXPOSE 22

WORKDIR /root
COPY ./id_rsa.pub /root/.ssh/authorized_keys

RUN chmod 700 ~/.ssh
RUN chmod 600 ~/.ssh/authorized_keys

COPY ./Makefile /usr/local/bin
COPY ./cpu-benchmark.cpp /usr/local/bin

RUN cd /usr/local/bin && make && cd ~

RUN conda install -y pandas pathos

COPY ./entry.sh /bin

RUN chmod +x /bin/entry.sh

FROM base AS builder

ARG CACHEBUST=1

COPY ./wfbench /usr/local/bin

# Install parsl
RUN git clone --depth 1 --branch scheduling_using_simulation https://github.com/jeff-yc-wong/parsl.git
RUN pip install parsl/

# Intall WfCommons
# RUN git clone --depth 1 --branch feature/wfbench_updates https://github.com/wfcommons/WfCommons.git
# RUN pip install WfCommons/

ENTRYPOINT ["/bin/entry.sh"]

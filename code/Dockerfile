FROM python:3.12-slim-bookworm

# Runtime dependencies required for the application
ARG CHROME_PACKAGE=google-chrome-stable_current_amd64.deb
RUN apt-get update -y
RUN apt-get install wget -y
RUN wget https://dl.google.com/linux/direct/$CHROME_PACKAGE
# Required to detect missing google chrome dependencies and install them again in the followign command
RUN (dpkg -i $CHROME_PACKAGE || true)
RUN apt-get install -f -y
RUN dpkg -i $CHROME_PACKAGE
RUN rm $CHROME_PACKAGE

WORKDIR /opt/price-monitor

# Copy the build application wheel file and install it as a package
COPY dist/*tar.gz price-monitor.tar.gz
RUN pip install price-monitor.tar.gz
RUN rm price-monitor.tar.gz

# Default log level
ENV LOGURU_LEVEL=INFO

VOLUME "/opt/price-monitor/data"
VOLUME "/opt/price-monitor/config"
CMD ["price-monitor"]

FROM python:3
# Create app & config directory
WORKDIR /app
RUN mkdir -p /app/src
# Install app dependencies
COPY src/requirements.txt ./

RUN pip install -r requirements.txt

# Bundle app source
COPY src /app/src

# Install config
RUN mkdir -p /app/config
#COPY config/config.yaml /app/config/

CMD [ "python", "/app/src/hubitat-mqtt.py" ]
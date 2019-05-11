FROM python:3
# Create app & config directory
WORKDIR /app
RUN mkdir -p /app/config

# Install app dependencies
COPY src/requirements.txt ./

RUN pip install -r requirements.txt

# Bundle app source
COPY src /app

# Install config
COPY config/config.yaml /app/config/

CMD [ "python", "hubitat-mqtt.py" ]
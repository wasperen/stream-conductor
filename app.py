import flask
import os
import subprocess
import datetime as dt
import json

app = flask.Flask(__name__)


def reload_config():
    proc = subprocess.Popen([NGINX_BIN, '-s', 'reload'], stderr=subprocess.PIPE)
    proc.wait()
    return proc.returncode, str(proc.stderr.readlines())


def create_stream_filename(configuration: dict) -> str:
    return STREAM_PREFIX + str(configuration['listen']) + '-' + configuration['proxy_pass'] + '.conf'


def parse_stream_definition(file: str):
    result = {}
    with open(file) as file:
        for l in file:
            parts = l.strip().split(' ')
            print(parts)
            if parts[0] == 'listen':
                result['listen'] = int(parts[1][:len(parts[1])-1])
            elif parts[0] == 'proxy_pass':
                result['proxy_pass'] = parts[1][:len(parts[1])-1]
    return result


def write_stream_definition(configuration: dict):
    stream_template = \
        'server {{ \n' + \
        '   # created {0}\n' + \
        '   listen {1};\n' + \
        '   proxy_pass {2};\n' + \
        '}}'
    stream_definition = stream_template.format(dt.datetime.now(), configuration['listen'], configuration['proxy_pass'])
    with open(STREAM_CONFIG_PATH + create_stream_filename(configuration), 'w') as file:
        file.write(stream_definition)
    return stream_definition


def delete_stream_definition(configuration: dict):
    os.remove(STREAM_CONFIG_PATH + create_stream_filename(configuration))


def get_stream_configurations():
    result = []
    for file in os.listdir(STREAM_CONFIG_PATH):
        print(file)
        if os.path.isfile(STREAM_CONFIG_PATH + file) and \
                file.startswith(STREAM_PREFIX) and \
                file.endswith('.conf'):
            result.append(parse_stream_definition(STREAM_CONFIG_PATH + file))
    return result


@app.route('/status')
def status():
    return json.dumps(dict(
        version=APP_VERSION,
        available_ports=str(PORT_RANGE)
    ))


@app.route('/getstreams')
def get_streams():
    return json.dumps(get_stream_configurations())


@app.route('/createstream/<int:port>/<string:backend>')
def create_stream(port, backend):
    configuration = {
        'listen': port,
        'proxy_pass': backend
    }
    write_stream_definition(configuration)
    code, stderr = reload_config()
    if code != 0:
        delete_stream_definition(configuration)
    return json.dumps(dict(
        result='ok' if code == 0 else 'error',
        errors=stderr
    ))


@app.route('/removestream/<int:port>')
def remove_stream(port: int):
    for configuration in get_stream_configurations():
        if configuration['listen'] == port:
            delete_stream_definition(configuration)
            code, stderr = reload_config()
            return json.dumps(dict(
                result='ok' if code == 0 else 'error',
                errors=stderr
            ))
    return json.dumps(dict(
        result='error',
        error='not found'
    ))


@app.route('/hasstream/<int:port>')
def has_stream(port: int):
    for configuration in get_stream_configurations():
        if configuration['listen'] == port:
            return json.dumps(dict(result='true'))
    return json.dumps(dict(result='false'))


@app.route('/getfreeport')
def get_free_port():
    claimed_ports = [configuration['listen'] for configuration in get_stream_configurations()]
    for port in PORT_RANGE:
        if port not in claimed_ports:
            return json.dumps(dict(result='ok', port=port))
    return json.dumps(dict(result='none available'))


if __name__ == '__main__':
    APP_VERSION = '0.1'
    STREAM_CONFIG_PATH = os.getenv('STREAM_CONFIG_PATH', '/etc/nginx/stream.d/')
    if not STREAM_CONFIG_PATH.endswith('/'):
        STREAM_CONFIG_PATH += '/'
    NGINX_BIN = os.getenv('NGINX_BIN', '/usr/sbin/nginx')
    STREAM_PREFIX = os.getenv('STREAM_PREFIX', '_conductor_')

    ports = os.getenv('PORT_RANGE', '9000-9999').strip().split('-')
    PORT_RANGE = range(int(ports[0]), int(ports[1]))

    BIND_ADDRESS = os.getenv('BIND_ADDRESS', '0.0.0.0')
    BIND_PORT = os.getenv('BIND_PORT', '5000')
    app.run(host=BIND_ADDRESS, port=BIND_PORT)

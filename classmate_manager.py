import fileinput
import os
import subprocess
import sys
import time
from bluezero import adapter
from bluezero import peripheral
from bluezero import device

UART_SERVICE = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
RX_CHARACTERISTIC = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
TX_CHARACTERISTIC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'


def wifi_connect(ssid, password=""):
    print("Connecting to WiFi...")
    command = ["nmcli", "dev", "wifi", "connect", f'{ssid}']
    if password:
        command.extend(["password", f'{password}'])
    try:
        subprocess.run(command, check=True)
        print("Connected to WiFi successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error connecting to WiFi: {e}")

def ip_config_dhcp(connection):
    if connection not in ['eth0', 'wlan0']:
        print("Invalid connection specified.")
        return

    interfaces_file = '/etc/network/interfaces'

    try:
        new_config_lines = [
            f'allow-hotplug {connection}\n',
            f'iface {connection} inet dhcp\n'
        ]

        # Leggi le configurazioni esistenti
        with open(interfaces_file, 'r') as file:
            existing_config = file.readlines()

        # Rimuovi le vecchie configurazioni per l'interfaccia specificata
        new_config = []
        found_interface = False
        for line in existing_config:
            if line.strip() == f'allow-hotplug {connection}':
                found_interface = True
            elif found_interface and line.strip().startswith('allow-hotplug'):
                found_interface = False
            if not found_interface:
                new_config.append(line)

        # Aggiungi le nuove configurazioni
        new_config.extend(new_config_lines)

        # Scrivi le nuove configurazioni nel file
        with open(interfaces_file, 'w') as file:
            file.writelines(new_config)

        # Riavvia il servizio di networking
        subprocess.run(['sudo', 'systemctl', 'restart', 'networking'], check=True)

    except FileNotFoundError:
        print("File not found:", interfaces_file)
    except Exception as e:
        print("An error occurred:", str(e))


def ip_config_static(connection, ipaddress, netmask, route_gateway, primary_dns):
    if connection not in ['eth0', 'wlan0']:
        print("Invalid connection specified.")
        return

    interfaces_file = '/etc/network/interfaces'

    try:
        new_config_lines = [
            f'allow-hotplug {connection}\n',
            f'iface {connection} inet static\n',
            f'    address {ipaddress}\n',
            f'    netmask {netmask}\n',
            f'    gateway {route_gateway}\n',
            f'    dns-nameservers {primary_dns}\n'
        ]

        # Leggi le configurazioni esistenti
        with open(interfaces_file, 'r') as file:
            existing_config = file.readlines()

        # Rimuovi le vecchie configurazioni per l'interfaccia specificata
        new_config = []
        found_interface = False
        for line in existing_config:
            if line.strip() == f'allow-hotplug {connection}':
                found_interface = True
            elif found_interface and line.strip().startswith('allow-hotplug'):
                found_interface = False
            if not found_interface:
                new_config.append(line)

        # Aggiungi le nuove configurazioni
        new_config.extend(new_config_lines)

        # Scrivi le nuove configurazioni nel file
        with open(interfaces_file, 'w') as file:
            file.writelines(new_config)

        # Riavvia il servizio di networking
        subprocess.run(['sudo', 'systemctl', 'restart', 'networking'], check=True)

    except FileNotFoundError:
        print("File not found:", interfaces_file)
    except Exception as e:
        print("An error occurred:", str(e))




def wifi_disconnect():
    os.system("nmcli dev disconnect wlan0")


def enable_wifi():
    os.system("nmcli radio wifi on")


def disable_wifi():
    os.system("nmcli radio wifi off")


def turn_on_bluetooth():
    subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], check=True)


def turnoff_device():
    subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)


def list_wifi_connections():
    try:
        # Esegui il comando nmcli per ottenere le informazioni sulle connessioni Wi-Fi disponibili
        result = subprocess.run(["nmcli", "device", "wifi", "list"], capture_output=True, text=True, check=True)

        # Estrai le informazioni sugli SSID delle connessioni Wi-Fi dalla stdout del risultato
        wifi_info = result.stdout.splitlines()[1:]

        # Stampare solo gli SSID delle connessioni Wi-Fi disponibili
        print("Available Wi-Fi SSIDs:")
        for line in wifi_info:
            ssid = line.split()[1]
            print(ssid)

    except subprocess.CalledProcessError as e:
        print(f"Error listing Wi-Fi connections: {e}")


def reboot_device():
    subprocess.run(['sudo', 'reboot'], check=True)

def get_active_connection_name():
    try:
        # Esegui il comando nmcli per ottenere le informazioni sulla connessione attiva
        result = subprocess.run(['nmcli', 'connection', 'show', '--active'], capture_output=True, text=True, check=True)

        # Analizza l'output per estrarre il nome della connessione attiva
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if line.strip():
                connection_name = line.split()[4]
                return connection_name

        # Se non viene trovata una connessione attiva, restituisci None
        return None

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None


def configure_btmgmt():
    try:

        subprocess.run(['sudo', 'rfkill', 'block', 'bluetooth'], check=True)

        subprocess.run(['sudo', 'rfkill', 'unblock', 'bluetooth'], check=True)

        subprocess.run(['sudo', 'hciconfig', 'hci0', 'down'], check=True)
        # Attendi un secondo per permettere al servizio di riavviarsi
        time.sleep(1)

        # Accendi il dispositivo Bluetooth
        subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], check=True)
        subprocess.run(['sudo', 'systemctl', 'stop', 'bluetooth'], check=True)

        subprocess.run(['sudo', 'systemctl', 'start', 'bluetooth'], check=True)
        subprocess.run(['sudo', 'systemctl', 'restart', 'bluetooth'], check=True)

        # Imposta le opzioni del dispositivo Bluetooth con btmgmt
        subprocess.run(['sudo', 'btmgmt', 'power', 'on'], check=True)
        subprocess.run(['sudo', 'btmgmt', 'discov', 'on'], check=True)
        subprocess.run(['sudo', 'btmgmt', 'connectable', 'on'], check=True)
        subprocess.run(['sudo', 'btmgmt', 'pairable', 'on'], check=True)
        subprocess.run(['sudo', 'btmgmt', 'io-cap', '3'], check=True)

        time.sleep(1)



    except subprocess.CalledProcessError as e:
        print(f"Errore durante la configurazione del Bluetooth: {e}")
    except Exception as ex:
        print(f"Errore non gestito durante la configurazione del Bluetooth: {ex}")



    except subprocess.CalledProcessError as e:
        print(f"Errore durante la configurazione del Bluetooth: {e}")
    except Exception as ex:
        print(f"Errore non gestito durante la configurazione del Bluetooth: {ex}")


class UARTDevice:
    device_address = None
    tx_obj = None

    @classmethod
    def on_connect(cls, ble_device: device.Device):
        print("Connected to " + str(ble_device.address))
        cls.device_address = ble_device.address

    @classmethod
    def on_disconnect(cls, adapter_address, device_address):
        print("Disconnected from " + device_address)
        configure_btmgmt()
        os.execv(__file__, sys.argv)

    @classmethod
    def disconnect_bluetooth(cls):
        try:
            subprocess.run(['sudo', 'hcitool', 'dc', cls.device_address], check=True)
            configure_btmgmt()
            print("Disconnection process completed.")
        except subprocess.CalledProcessError as e:
            print(f"Error disconnecting Bluetooth: {e}")
            return

        # Aggiungi un ritardo prima di riconfigurare l'adattatore Bluetooth
        time.sleep(5)

        try:
            configure_btmgmt()
        except Exception as ex:
            print(f"Error configuring Bluetooth after disconnection: {ex}")

    @classmethod
    def uart_notify(cls, notifying, characteristic):
        print('Nell notify:', "notify")
        if notifying:
            print('Nell notify:', characteristic)
            cls.tx_obj = characteristic
        else:
            cls.tx_obj = None
        print('UART Notify called!')

    @classmethod
    def uart_write(cls, value, options):
        message = bytes(value).decode('utf-8')
        print('Received:', message)

        if message == "turn_off":
            turnoff_device()
        elif message == "reboot":
            reboot_device()
        elif message == "disconnect":
            cls.disconnect_bluetooth()
        elif message == "wifi_list":
            wifi_list = cls.get_wifi_list()
            if wifi_list:
                wifi_list_str = ','.join(wifi_list)
                cls.tx_obj.set_value(wifi_list_str)
                print('Sent Wi-Fi list:', wifi_list_str)
            else:
                print('No Wi-Fi networks found')
        elif message == "info":
            system_info = cls.get_system_info()
            if system_info:
                system_info_str = '\n'.join(system_info)
                print('System info to send:', system_info_str)  # Debugging: Check system info to send
                cls.tx_obj.set_value("hello")
                print('Sent system info:', )
            else:
                print('Failed to retrieve system info')
        else:
            message_components = message.split(',')
            if message_components[0] == "wifi":
                print('Nel wifi:', "wifi")
                if len(message_components) < 3:
                    wifi_connect(message_components[1])
                else:
                    wifi_connect(message_components[1], message_components[2])
            elif message_components[0] == "dhcp":
                print('Nel dhcp:', "dhcp")
                ip_config_dhcp(message_components[1])
            elif message_components[0] == "static":
                print('Nel static:', "static")
                ip_config_static(message_components[1], message_components[2], message_components[3], message_components[4],
                          message_components[5],)
            else:
                print("Invalid message format")

    @staticmethod
    def get_wifi_list():
        try:
            result = subprocess.run(["nmcli", "device", "wifi", "list"], capture_output=True, text=True, check=True)
            wifi_info = result.stdout.splitlines()[1:]
            return [line.split()[1] for line in wifi_info]
        except subprocess.CalledProcessError as e:
            print(f"Error listing Wi-Fi connections: {e}")
            return None

    @staticmethod
    def get_system_info():
        try:
            print('Nell info:', "info")
            info = []
            # Get system hostname
            hostname = subprocess.run(["hostname"], capture_output=True, text=True, check=True)
            info.append("Hostname: " + hostname.stdout.strip())
            # Get MAC address
            mac_address = subprocess.run(["cat", "/sys/class/net/eth0/address"], capture_output=True, text=True,
                                         check=True)
            info.append("MAC Address: " + mac_address.stdout.strip())
            # Get connected Wi-Fi network
            wifi_network = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True, check=True)
            info.append("Connected Wi-Fi Network: " + wifi_network.stdout.strip())
            print('Nell info:', info)
            return info
        except subprocess.CalledProcessError as e:
            print(f"Error getting system info: {e}")
            return None


def main(adapter_address):
    configure_btmgmt()
    list_wifi_connections()
    ble_uart = peripheral.Peripheral(adapter_address, local_name='Classmate')

    # Aggiungi nuove caratteristiche
    ble_uart.add_service(srv_id=1, uuid=UART_SERVICE, primary=True)
    ble_uart.add_characteristic(srv_id=1, chr_id=1, uuid=RX_CHARACTERISTIC,
                                value=[], notifying=False,
                                flags=['write', 'write-without-response'],
                                write_callback=UARTDevice.uart_write,
                                read_callback=None,
                                notify_callback=None)
    ble_uart.add_characteristic(srv_id=1, chr_id=2, uuid=TX_CHARACTERISTIC,
                                value=[], notifying=False,
                                flags=['notify', 'write'],  # Aggiunto 'write' alle flags
                                notify_callback=UARTDevice.uart_notify,
                                read_callback=None,
                                write_callback=None)

    ble_uart.on_connect = UARTDevice.on_connect

    ble_uart.publish()


if __name__ == '__main__':
    disable_wifi()
    enable_wifi()
    main(list(adapter.Adapter.available())[0].address)

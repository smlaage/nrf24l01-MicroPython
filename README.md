Demo of a wireless client/server connection with the Raspberry Pi Pico and the NRF24L01 transceiver

This project implements a wireless client/server connection based on the NRF24L01 transceiver and the Raspberry Pi Pico. The software is implemented in MicroPython and uses the nrf24l01 library. The project could serve as an example of a remote control system for a model car or something similar. In such an environment, the server represents a handheld controller, while the client controls the car. 

Server: The server has an analog X/Y joystick and 3 push buttons. In addition, there are 3 LEDs that can be activated by the client, e.g. to indicate the status of the client.

Client: At this stage, the client operates a servo motor that can be used for steering. Other activators are not yet implemented. The client also contains a button, e.g. a bumper sensor. The value of the button can be transmitted to the server. 

Communication protocol: Communication is based on data packets of 8 bytes, which are exchanged bidirectionally. As soon as the server is in operation, it waits for messages coming from the client. This means that all communication is initiated by the client. The very simplified protocol provides for two different commands, which are distinguished by the first byte of the message. 

Character 'D' for "Retrieve data": This causes the server to retrieve the current data from joystick and buttons and return it to the client. The returned message uses bytes 0 and 1 for the x-position (16-bit integer), bytes 2 and 3 for the y-position (16-bit integer) and byte 4 for the status of the buttons (one bit per button). The client uses the x-position to control the servo. The other data is ignored at this stage of development. Typically, the y-position would be used to control the motor of the model car via PWM.

Character 'L' for "Set LEDs": This command is used to set the LEDs on the server. LEDs 0, 1 and 2 are controlled via bytes 1, 2 and 3 of the message respectively. A value of 0 stands for LED off and any other value for LED on.

Speed and error handling: The client performs 20 data queries per second, which enables reasonably smooth control of the model car. The software of both systems contains a two-color LED that indicates whether communication is going well (green) or whether an error has occurred (red). The software shown here sets the transmission power to a medium level (POWER_2) and the speed to a relatively low value (SPEED_250K). Experiments have shown good results over long distances. If necessary, the transmission power can be increased to the maximum (POWER_3).

import UART
try:
    uart = UART(1, baudrate=9600, bits=8, parity=None, stop=1, tx=16, rx=17, flow=UART.XON_XOFF)
    print("XON/XOFF flow control is supported.")
except ValueError as e:
    print("XON/XOFF flow control is not supported.")
    print(e)
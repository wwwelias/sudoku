import pyads
AmsNetId = '10.15.96.76.1.1'
# connect to plc and open connection
plc = pyads.Connection(AmsNetId, pyads.PORT_TC3PLC1)
plc.open()

# read int value by name
i = plc.read_by_name("GVL.bSudoku", pyads.PLCTYPE_BYTE * 81)
print(i)

result = '096002007100000090300060000000800003029040080010000000600000000000007500084020030'
# write int value by name
#plc.write_by_name("GVL.sSudokuResult", result)

# close connection
plc.close()
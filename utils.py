from struct import unpack

def readint(self):
  data = self.file.read(4)
  return unpack('>I', data)[0]

def readshort(self):
  data = self.file.read(2)
  return unpack('>H', data)[0]

def readbyte(self):
  data = self.file.read(1)
  return unpack('B', data)[0]

def read24bit(self):
  b1, b2, b3 = unpack('3B', self.file.read(3))
  return (b1 << 16) + (b2 << 8) + b3

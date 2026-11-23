import qrcode
img=qrcode.make("ftp://example.com")
img.save("exampleftp.png")

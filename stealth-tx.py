#!/usr/bin/python
import os
import sys

# Generate new key to begin
os.system("sx newkey > key")
os.system("cat key | sx addr")

raw_input("Send 0.001 BTC to that address before continuing...[ENTER]")

# Create recipient stealth info
os.system("sx stealth-new > stealth")
with open("stealth") as f:
    for line in f:
        label = "Address: "
        if line.startswith(label):
            stealth_address = line[len(label):-1]
            break

# Create sender stealth info
os.system("sx stealth-send %s > stealth.send" % stealth_address)
with open("stealth.send") as f:
    for line in f:
        label = "Ephemeral pubkey: "
        if line.startswith(label):
            ephemkey = line[len(label):-1]
            continue
        label = "Address: "
        if line.startswith(label):
            address = line[len(label):-1]
            break

tx_input = raw_input("Enter tx input as HASH:INDEX for payment:")

if len(tx_input) < 66 or tx_input[64] != ":":
    print >> sys.stderr, "Invalid tx input"
    sys.exit(-1)

try:
    tx_input[:64].decode("hex")
except TypeError:
    print >> sys.stderr, "Invalid tx input"
    sys.exit(-1)

try:
    int(tx_input[65:])
except ValueError:
    print >> sys.stderr, "Invalid tx input"
    sys.exit(-1)

# Create bash script to generate stealth tx
f = open("generate.sh", "w")
print >> f, "#!/bin/bash"
print >> f, "EPHEMKEY=%s" % ephemkey
# version=06 nonce=deadbeef ephemkey
print >> f, "EPHEM_OUT=$(sx rawscript return [ 06deadbeef$EPHEMKEY ])"
print >> f
print >> f, "INPUT=%s" % tx_input
print >> f, "ADDRESS=%s" % address
print >> f, "AMOUNT=$(sx satoshi 0.0009)"
print >> f, "sx mktx tx --input $INPUT --output $EPHEM_OUT:0 --output $ADDRESS:$AMOUNT"
print >> f
print >> f, "DECODED_ADDR=$(cat key | sx addr | sx decode-addr)"
print >> f, "PREVOUT_SCRIPT=$(sx rawscript dup hash160 [ $DECODED_ADDR ] equalverify checksig)"
print >> f, "SIGNATURE=$(cat key | sx sign-input tx 0 $PREVOUT_SCRIPT)"
print >> f, "INPUT_SCRIPT=$(sx rawscript [ $SIGNATURE ] [ $(cat key | sx pubkey) ])"
print >> f, "sx set-input tx 0 $INPUT_SCRIPT > signed-tx"
f.close()

# Run the script
os.system("chmod +x generate.sh")
os.system("./generate.sh")

print
print "Now broadcast your tx using http://eligius.st/~wizkid057/newstats/pushtxn.php"
os.system("cat signed-tx")


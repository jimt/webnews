import os

def backupfile(filename, extension=".bak"):
    """ create a backupfile, returning (fin, fout) renaming original """

    backname = filename+extension

    try:
        os.remove(backname)
    except:
        pass # maybe nothing to delete

    os.rename(filename, backname)

    try:
        fin = open(backname, "r")
    except:
        print "Unable to open input file: %s" % backname

    try:
        fout = open(filename, "w")
    except:
        print "Unable to create output file: %s" % filename

    return (fin, fout)

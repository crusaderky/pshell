import pshell as sh


BLURB = 'helloworld'


def test_concatenate1(tmpdir):
    # Output file already exists and is non-empty. Files end without a newline.
    filenames = [
        '%s/%d.txt' % (tmpdir, pos)
        for pos, _ in enumerate(BLURB)
    ]

    for fname, char in zip(filenames, BLURB):
        with open(fname, 'w') as fh:
            fh.write(char)

    sh.concatenate(*filenames)

    with open(filenames[0]) as fh:
        concatenated_file_contents = fh.readlines()

    assert concatenated_file_contents == [char + '\n' for char in BLURB]


def test_concatenate2(tmpdir):
    # Output file already exists and is non-empty. Files end with a newline.
    filenames = [
        '%s/%d.txt' % (tmpdir, pos)
        for pos, _ in enumerate(BLURB)
    ]

    for fname, char in zip(filenames, BLURB):
        with open(fname, 'w') as fh:
            fh.write(char + '\n')

    sh.concatenate(*filenames)

    with open(filenames[0]) as fh:
        concatenated_file_contents = fh.readlines()

    assert concatenated_file_contents == [char + '\n' for char in BLURB]


def test_concatenate3(tmpdir):
    # Output file already exists and it is empty
    filenames = [
        '%s/%d.txt' % (tmpdir, pos)
        for pos, _ in enumerate(BLURB)
    ]

    with open(filenames[0], 'w') as fh:
        pass
    for fname, char in zip(filenames[1:], BLURB[1:]):
        with open(fname, 'w') as fh:
            fh.write(char)

    sh.concatenate(*filenames)

    with open(filenames[0]) as fh:
        concatenated_file_contents = fh.readlines()

    assert concatenated_file_contents == [char + '\n' for char in BLURB[1:]]


def test_concatenate4(tmpdir):
    # Output file does not already exist
    filenames = [
        '%s/%d.txt' % (tmpdir, pos)
        for pos, _ in enumerate(BLURB)
    ]

    for fname, char in zip(filenames[1:], BLURB[1:]):
        with open(fname, 'w') as fh:
            fh.write(char)

    sh.concatenate(*filenames)

    with open(filenames[0]) as fh:
        concatenated_file_contents = fh.readlines()

    assert concatenated_file_contents == [char + '\n' for char in BLURB[1:]]

extern "C" int nnsocketFcntl(int, int, int);

extern "C" int func_613e5718(int fd, int arg1, int arg2) {
    int cmd = (arg1 == 0) ? 0x2 : 0x802;
    return nnsocketFcntl(fd, 4, cmd);
}
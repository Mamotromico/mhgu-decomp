extern "C" int func_6130b3ac(unsigned x) {
    int a = 0;
    int b = 0;
    if (x < 0x20) b = 1;
    unsigned y = x - 0xfd;
    if (y < 3) a = 1;
    return a | b;
}
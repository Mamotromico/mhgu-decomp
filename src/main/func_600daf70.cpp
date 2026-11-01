struct func_600daf70_input {
    unsigned char padding[4];
    unsigned short value;
};

extern "C" int func_600daf70(const func_600daf70_input* p) {
    unsigned int v = p->value & 0x1fU;
    if (v == 0xbU) {
        return 1;
    }
    if (v == 0xdU) {
        return 1;
    }
    return 0;
}
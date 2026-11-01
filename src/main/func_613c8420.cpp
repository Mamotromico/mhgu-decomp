struct Data {
    unsigned char pad[0x30];
    unsigned char value;
};

extern "C" int func_613c8420(Data *p) {
    if (p == 0)
        return 0;
    return p->value != 0;
}
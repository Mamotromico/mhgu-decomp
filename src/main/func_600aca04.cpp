struct S {
    char pad[0x4e];
    unsigned short value;
};

extern "C" int func_600aca04(int, S *s) {
    if (s == 0)
        return -1;

    unsigned short value = s->value;
    if (value == 0)
        return -1;

    return value;
}
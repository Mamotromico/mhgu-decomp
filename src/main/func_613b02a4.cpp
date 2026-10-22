struct func_613b02a4_s {
    char pad[0x1c];
    unsigned int field;
};

extern "C" int func_613b02a4(func_613b02a4_s* s) {
    return s->field == 0xfd ? 0 : 1;
}
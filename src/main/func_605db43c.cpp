struct func_605db43c_obj {
    unsigned char pad[0x4c];
    unsigned char field;
};

extern "C" void func_605db43c(struct func_605db43c_obj *dst, const unsigned char *src) {
    dst->field = *src;
}
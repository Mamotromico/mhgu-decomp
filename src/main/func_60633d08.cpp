struct func_60633d08_obj {
    unsigned char pad[0x4c];
    volatile unsigned int field_4c;
    volatile unsigned int field_50;
};

extern "C" void func_60633d08(struct func_60633d08_obj *obj, unsigned int a, unsigned int b) {
    obj->field_4c = a;
    obj->field_50 = b;
}
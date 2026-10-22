struct sub_6009db38_inner {
    char pad_0[0x3a0];
    unsigned short field_3a0;
};

struct sub_6009db38_outer {
    char pad_0[0x1428];
    sub_6009db38_inner *ptr_1428;
};

extern "C" void func_6009db38(sub_6009db38_outer *obj, unsigned short value)
{
    sub_6009db38_inner *inner = obj->ptr_1428;
    inner->field_3a0 |= value;
}
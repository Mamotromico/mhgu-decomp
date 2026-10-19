struct sub_600bd52c_inner {
    unsigned char pad[0x524];
    unsigned char field;
};

struct sub_600bd52c_outer {
    unsigned char pad[0x1428];
    sub_600bd52c_inner *ptr;
};

extern "C" sub_600bd52c_inner *func_600bd52c(sub_600bd52c_outer *arg) {
    sub_600bd52c_inner *p = arg->ptr;
    p->field = 0;
    return p;
}
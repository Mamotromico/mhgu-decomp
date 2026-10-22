struct func_60b0cab0_elem {
    unsigned int field0;
    unsigned int field4;
};

struct func_60b0cab0_obj {
    unsigned char pad[0x50];
    func_60b0cab0_elem arr[1];
};

extern "C" void func_60b0cab0(func_60b0cab0_obj *p, unsigned int i, unsigned int v) {
    p->arr[i].field0 = (unsigned short)v;
    p->arr[i].field4 = 0;
}
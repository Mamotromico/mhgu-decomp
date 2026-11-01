struct inner_struct {
    char pad0[0x10];
    unsigned int val0;
    unsigned int val1;
    unsigned int val2;
};

struct outer_struct {
    char pad0[0x1428];
    struct inner_struct * volatile ptr;
};

extern "C" void func_6007d9bc(struct outer_struct *obj) {
    obj->ptr->val0 = 0;
    obj->ptr->val1 = 0;
    obj->ptr->val2 = 0;
}
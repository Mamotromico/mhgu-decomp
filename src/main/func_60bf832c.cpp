struct func_60bf832c_inner {
    unsigned char pad[0x14];
    void *value;
};

struct func_60bf832c_outer {
    struct func_60bf832c_inner *ptr;
};

extern "C" void *func_60bf832c(struct func_60bf832c_outer *arg) {
    return arg->ptr->value;
}
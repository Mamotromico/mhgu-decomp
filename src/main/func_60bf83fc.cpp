struct func_60bf83fc_obj {
    char pad[0xad4];
    void *value;
};

struct func_60bf83fc_arg {
    struct func_60bf83fc_obj *obj;
};

extern "C" void *func_60bf83fc(struct func_60bf83fc_arg *arg) {
    return arg->obj->value;
}
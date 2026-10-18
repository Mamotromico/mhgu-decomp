struct func_6070e834_obj {
    struct func_6070e834_vtable *vtable;
};

struct func_6070e834_vtable {
    unsigned char pad[0x48];
    int (*call)(struct func_6070e834_obj *);
};

extern "C" int func_6070e834(struct func_6070e834_obj *obj)
{
    return obj->vtable->call(obj);
}
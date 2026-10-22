struct Sender {
    int pad0;
    void *arg;
};

struct VTable {
    char pad[12];
    void (*callback)(void *, void *);
};

struct Obj {
    VTable *vtable;
};

extern "C" void func_60107a14(Sender *sender, Obj *obj) {
    obj->vtable->callback(obj, sender->arg);
}
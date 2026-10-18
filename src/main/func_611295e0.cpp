struct table_t {
    char pad[0x208];
    void (*f)(void *, void *);
};

struct object_t {
    struct table_t *table;
};

extern "C" void func_611295e0(struct object_t *self, void *arg) {
    self->table->f(self, arg);
}
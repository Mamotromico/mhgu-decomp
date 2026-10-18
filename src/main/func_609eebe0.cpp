struct func_609eebe0_obj {
    char pad[0xa0];
    void **items;
};

extern "C" void *func_609eebe0(const struct func_609eebe0_obj *obj, unsigned int index) {
    return obj->items[index];
}
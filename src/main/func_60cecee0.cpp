struct func_60cecee0_obj {
    char pad[0x7c];
    void **table;
};

extern "C" void *func_60cecee0(struct func_60cecee0_obj *obj, unsigned int index) {
    return obj->table[index];
}
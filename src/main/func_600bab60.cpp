extern "C" int func_600bab60(void *self, unsigned idx) {
    if (idx >= 8) {
        char *vtable = *(char **)self;
        int (*fn)(void *, unsigned) = *(int (**)(void *, unsigned))(vtable + 0x314);
        return fn(self, idx);
    }
    char *base = *(char **)((char *)self + 0x1428);
    return *(int *)(base + 0x418 + idx * 4);
}
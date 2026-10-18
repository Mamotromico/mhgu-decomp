struct inner {
    unsigned char pad[0x9fc];
    void *value;
};

struct outer {
    struct inner *ptr;
};

extern "C" void *func_60bf8408(const struct outer *self)
{
    return self->ptr->value;
}
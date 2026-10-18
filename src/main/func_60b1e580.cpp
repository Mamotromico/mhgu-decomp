struct func_60b1e580_obj {
    unsigned char pad[0x40];
    void **items;
};

extern "C" void *func_60b1e580(struct func_60b1e580_obj *self, unsigned int index)
{
    return self->items[index];
}
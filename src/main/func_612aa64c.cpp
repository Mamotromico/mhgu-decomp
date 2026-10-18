struct S {
    unsigned char pad[0x58];
    void **table;
};

extern "C" void *func_612aa64c(const struct S *s, unsigned int index)
{
    return s->table[index];
}
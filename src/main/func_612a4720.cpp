struct func_612a4720_inner {
    void *value;
};

struct func_612a4720_outer {
    unsigned char pad[4];
    struct func_612a4720_inner *inner;
};

extern "C" void *func_612a4720(struct func_612a4720_outer *outer)
{
    return outer->inner->value;
}
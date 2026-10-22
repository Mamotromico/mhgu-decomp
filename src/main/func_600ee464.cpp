struct func_600ee464_target;

struct func_600ee464_B;

struct func_600ee464_target {
    unsigned char pad0[0xc];
    void (*callback)(struct func_600ee464_B *, void *);
};

struct func_600ee464_B {
    struct func_600ee464_target *target;
};

struct func_600ee464_A {
    unsigned char pad0[4];
    void *arg;
};

extern "C" void func_600ee464(struct func_600ee464_A *a, struct func_600ee464_B *b)
{
    struct func_600ee464_target *target = b->target;
    target->callback(b, a->arg);
}
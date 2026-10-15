struct Container {
    char pad[0x10];
    unsigned long long value;
};

extern "C" unsigned long long func_6134c36c(const struct Container *p) {
    return p->value;
}
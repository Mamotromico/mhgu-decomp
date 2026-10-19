struct Dest {
    unsigned int word0;
    unsigned int word4;
    unsigned short half8;
};

extern "C" void func_61364eb8(Dest* d, unsigned int a, unsigned int b) {
    d->word0 = a;
    d->word4 = b;
    d->half8 = 0;
}
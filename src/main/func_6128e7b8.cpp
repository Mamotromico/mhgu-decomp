extern "C" {
int _ZN2nn6socket8ShutdownEii(int, int);
}

struct S {
    char pad[8];
    int fd;
};

extern "C" int func_6128e7b8(S *s) {
    return (unsigned)_ZN2nn6socket8ShutdownEii(s->fd, 2) >> 31;
}
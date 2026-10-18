struct func_604fc6c0_s {
    char pad[0xec];
    unsigned int *array;
};

extern "C" unsigned int func_604fc6c0(struct func_604fc6c0_s *self, int index) {
    return self->array[index];
}
package com.example.UserAuth.repositories;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.UserAuth.Entity.User;
import com.example.UserAuth.dto.UserDto;

public interface UserRepository extends JpaRepository<User, Long> {

 User findByUsername(String username);

 User save(UserDto userDto);
}